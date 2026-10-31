pragma solidity 0.5.12;

contract Pool7276 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public shares;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        reserve += msg.value;
    }
    bool private locked;

    function withdraw(uint256 amount) public {
        require(!locked);
        locked = true;
        require(shares[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
        shares[msg.sender] -= amount;
        reserve -= amount;
        locked = false;
    }

    function totalDeposits() public view returns (uint256) { return reserve; }

    function ownerOf_() public view returns (address) { return owner; }
}
