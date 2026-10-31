pragma solidity 0.5.12;

contract Fund8802 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public credit;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        supply += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(credit[msg.sender] >= amount);
        msg.sender.transfer(amount);
        credit[msg.sender] -= amount;
        supply -= amount;
    }

    function ownerOf_() public view returns (address) { return owner; }
}
