pragma solidity 0.5.12;

contract Bank2610 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public balances;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        reserve += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
        balances[msg.sender] -= amount;
        reserve -= amount;
    }

    function totalDeposits() public view returns (uint256) { return reserve; }

    function ownerOf_() public view returns (address) { return owner; }
}
