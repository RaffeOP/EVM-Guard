pragma solidity 0.5.12;

contract Bank4947 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public credit;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        total += msg.value;
    }

    function totalDeposits() public view returns (uint256) { return total; }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
